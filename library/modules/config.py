import re
from os import path
import datetime
from typing import Union

import yaml

from library.modules.code_patterns import AttDict


def load_yaml(file: str) -> dict:
    """
    Carga en memoria un fichero .yml y lo devuelve en forma de diccionario.
    :param file: Ruta hasta el fichero que se desea cargar en memoria.
    :return: Contenido del fichero en forma de diccionario.
    """
    with open(file, 'r') as stream:
        configuration = yaml.load(stream, Loader=yaml.SafeLoader)
    return configuration


class ConfigBase(AttDict):
    """
    Base class for the config_path object.
    It must be innerited by the custom config_path object to receive several benefits:
        1) Native handling of base and default configurations, defined by their paths.
        2) Inneritance of the AttDict behaviour for improved dictionary interface.
        3) Support for automatic execution of post processingand compliance checks routines.
        4) PrettyPrint native method.
    """

    @staticmethod
    def load_yaml(path_: str):
        assert path.basename(path_)[-5:] == '.yaml', 'config_path does\'t lead to a .yaml file.\n' \
                                                     'config_path: {}'.format(path)
        return load_yaml(path_)

    # noinspection PyShadowingNames
    @staticmethod
    def load_bbdd(path_: str):
        return load_yaml(path_)

    load_methods = {'yaml': 'load_yaml',
                    'jump_BBDD': 'load_bbdd'}

    def load(self, load_method: str, *args):
        return getattr(self, self.load_methods[load_method])(*args)

    def __init__(self, config_path: Union[str, AttDict], default_config_path: str = None,
                 add_extra_attributes: bool = True, load_method: str = 'yaml', **kwargs):
        """
        Initialization of the object.

        Base and default configurations are merged, giving prevalence to base attributes whenever they exist, but
        adding those attributes in the default configuration file when not explicitly declared on the base configuration.

        date, config_path and default_config_path attributes are automatically added to the object.
        :param config_path: Path to the configuration file.
        :param default_config_path: Optional. Path to the default configuration file.
        :param add_extra_attributes: Prevent the addition of date, config_path and default_config_path attributes to
                                     the object.
        """
        if isinstance(config_path, dict):  # Initialization through dict
            base_configuration = config_path
        else:
            base_configuration = self.load(load_method, config_path)
            base_configuration = self.coalesce_parent_config(base_configuration, load_method=load_method)

            if default_config_path is not None:
                assert path.basename(default_config_path)[-5:] == '.yaml', \
                    'default_config_path does\'t lead to a .yaml file.\n' \
                    'default_config_path: {}'.format(default_config_path)
                default_configuration = self.load(load_method, default_config_path)
                default_configuration = self.coalesce_parent_config(default_configuration, load_method=load_method)
                base_configuration = self.__coalesce_dicts__(base_configuration, default_configuration)

            if add_extra_attributes:
                base_configuration = self.__coalesce_dict_keys__(base_configuration, 'date', datetime.datetime.now())
                base_configuration = self.__coalesce_dict_keys__(base_configuration, 'config_path', config_path)
                base_configuration = self.__coalesce_dict_keys__(base_configuration, 'default_config_path',
                                                                 default_config_path)
            if base_configuration.__contains__('_parent_config'):
                del base_configuration['_parent_config']
        super().__init__(base_configuration, **kwargs)

    def copy(self) -> AttDict:
        return type(self)(self)

    @staticmethod
    def __coalesce_dict_keys__(dict_, k, v):
        if k not in dict_.keys():
            dict_[k] = v
        return dict_

    @staticmethod
    def __coalesce_dicts__(dict_left, dict_right):
        for key in [_ for _ in dict_right.keys() if _ not in dict_left.keys()]:
            dict_left[key] = dict_right[key]
        return dict_left

    def coalesce_parent_config(self, configuration: dict, load_method: str) -> dict:
        """
        If configuration object contains a "_parent_config" key, parse a new configuration object using its value as the
        loading path and use the new configuration file as a sort of "default configuration".
        The values defined on the current configuration always take precedence if there were also defined on the parent.

        :param configuration: A configuration object.
        :param load_method: Loading method to parse text configuration file.
        :return:
        """
        if configuration.__contains__('_parent_config'):
            parent_configuration = ConfigBase(config_path=configuration['_parent_config'],
                                              add_extra_attributes=False, load_method=load_method)

            configuration = self.__coalesce_dicts__(configuration, parent_configuration)
        return configuration

    def walk(self):
        """
        Yield all values nested on the configuration object.
        :return: A tuple containing (The_parent_object, the_key_name, the_key_value)
        """
        for k, v in self.items():
            yield from self._walk(self, k, v)

    def _walk(self, container, k, v):
        if isinstance(v, str):
            yield container, k, v
        elif isinstance(v, list):
            for i, vv in enumerate(v):
                yield from self._walk(v, i, vv)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                yield from self._walk(v, kk, vv)

    def transform_walk_attribute(self, att, func):
        """
        Generator. Yields all the values defined within the attribute 'att'.
        If a list or dict, execute recursively. If not, return the value transformed using func.
        Used to post process them even when nested.

        :param att: the config att referenced by other atts
        :param func: Function to apply to the attribute to transform it.
        :return: None
        """
        if isinstance(att, dict):
            att = {k: self.transform_walk_attribute(v, func) for k, v in att.items()}
        elif isinstance(att, list):
            att = [self.transform_walk_attribute(v, func) for v in att]
        else:
            att = func(att)
        return att

    def inject_dynamic_attributes(self, att_dict: dict):
        """
        Use <att_dict> to search injections on the configuration values with the form of <injection_name>.
        The injection placeholders will then be replaced by the corresponding values defined on the dictionary.
        Example:
        configuration value: s3://<bucket>/<brand>/table_name
        att_dict = {'bucket': 'Example_bucket',
                    'brand': 'brand1'}
        new configuration value: s3://Example_bucket/brand1/table_name
        """
        p = re.compile('<(.+?)>')

        for k, v in self.items():
            self[k] = self.transform_walk_attribute(v, lambda x: self.inject_attribute(x, att_dict, p))

    def inject_attribute(self, x, att_dict: dict, p):
        if isinstance(x, str):
            while len(p.findall(x)) > 0:  # This is required for recurrent replacement
                for kwarg in p.findall(x):
                    replacement = self[kwarg[1:]] if kwarg[0] == '.' else att_dict[kwarg]
                    if self.detect_internal_definition_dependencies(replacement):
                        replacement = f'<{replacement}>'
                    x = x.replace(f'<{kwarg}>', replacement)
        return x

    def detect_internal_definition_dependencies(self, value) -> bool:
        boolean = False
        if isinstance(value, str) and '.' in value:
            first_level, second_level = value.split('.')
            if first_level and first_level in self.keys():  # example: value is colnames.DATE  -> value = conf.colnames[DATE]
                boolean = True
            elif not first_level and second_level in self.keys():  # example: value is .date_col -> value = conf.date_col
                boolean = True
        return boolean

    def resolve_internal_definition_dependencies(self, value):
        if isinstance(value, str) and '.' in value:
            first_level, second_level = value.split('.')
            if first_level and first_level in self.keys():  # example: value is colnames.DATE  -> value = conf.colnames[DATE]
                value = self[first_level][second_level]
            elif not first_level and second_level in self.keys():  # example: value is .date_col -> value = conf.date_col
                value = self[second_level]
        return value

    def resolve_internal_definition_dependencies_recursive(self, att):
        """
        Fixes the value of any attribute to the value of another one, allowing the definition of internal dependencies.
        Example 1:
            colnames:
                DATE: day
                DAYDATE: daydate
            temporal_col: colnames.DATE
            (on post_process) self.resolve_internal_definition_dependencies_recursive('colnames') ->
            -> now temporal_col get the value: day
        Example 2:
            date_col: day
            temporal_col: .date_col
            (on post_process) self.resolve_internal_definition_dependencies_recursive('colnames') ->
            -> now temporal_col get the value: day
        :param att: the config att referenced by other atts
        :return: None
        """

        self[att] = self.transform_walk_attribute(self[att], self.resolve_internal_definition_dependencies)

    def _customize_param(self, att, versionables: dict, versions: dict):
        while isinstance(att, dict):
            versionable = False
            for topic, options in versionables.items():
                if all([k == 'default' or k in options for k in att.keys()]):  # dictionary is defining a versionable
                    if versions[topic] in att.keys():
                        att = att[versions[topic]]
                    else:
                        att = att['default']
                    versionable = True
                    break
            if not versionable:
                break
            # att = {k: self._customize_param(v, versionables=versionables, versions=versions)
            #        for k, v in att.items()}
        if isinstance(att, list):
            att = [self._customize_param(v, versionables=versionables, versions=versions) for v in att]
        elif isinstance(att, dict):
            att = {k: self._customize_param(v, versionables=versionables, versions=versions) for k, v in att.items()}
        return att

    def customize_param(self, att, versionables: dict, versions: dict):
        self[att] = self._customize_param(self[att], versionables=versionables, versions=versions)

    def customize_params(self, versions: dict):
        versionables = self.base_configuration.post_process_possible_values
        for att in self:
            try:
                self.customize_param(att, versionables=versionables, versions=versions)
            except KeyError:
                raise KeyError(f'Config variable {att} has no version for {versionables}')
        for k, v in versions.items():
            self[k] = v
