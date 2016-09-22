__author__ = 'thor'

import numpy as np
from json import JSONEncoder, dump, dumps
from datetime import datetime

# default_as_is_types = (list, np.ndarray, tuple, dict, float, int)
default_as_is_types = (list, np.ndarray, tuple, dict, float, int, set, np.int32,
                       basestring, np.matrixlib.defmatrix.matrix)


def trailing_underscore_attributes(obj):
    return [k for k in obj.__dict__ if k[-1] == '_']


def get_model_attributes(model,
                         include=(),
                         exclude=(),
                         model_name_as_dict_root=True,
                         as_is_types=default_as_is_types):
    """
    Export parameters of the model (or any object) to a dict.
    :param include: list of attributes to include (the function will automatically include attributes ending with
    an underscore
    :param exclude: list of attributes to exclude (to exclude underscore suffixed attributes
    :param model_name_as_dict_root: Whether to wrap the dict into a dict whose single key is the name of the model
    :param as_is_types: Types to take as is (all others will be passed on to get_model_attributes recursively
    :param version: String to include in the "version" field of the json
    :return: Nothing if dumping to json file, or the json string if argument filepath=None
    """
    if isinstance(model, as_is_types):
        return model
    else:
        attribute_set = set(trailing_underscore_attributes(model)).union(include).difference(exclude)
        states = {k: get_model_attributes(model.__getattribute__(k),
                                          include,
                                          exclude,
                                          model_name_as_dict_root,
                                          as_is_types) for k in attribute_set}
        if model_name_as_dict_root:
            return {model.__class__.__name__: states}
        else:
            return states


def get_model_attributes_dict_for_json(model,
                                       include=(),
                                       exclude=(),
                                       model_name_as_dict_root=True,
                                       as_is_types=default_as_is_types):
    if isinstance(model, as_is_types):
        return model
    elif isinstance(model, np.ndarray):
        return model.tolist()
    else:
        return get_model_attributes(model,
                                    include,
                                    exclude,
                                    model_name_as_dict_root,
                                    as_is_types
                                    )


def export_model_params_to_json(model,
                                include=(),
                                exclude=(),
                                model_name_as_dict_root=True,
                                as_is_types=default_as_is_types,
                                filepath='',
                                version=None,
                                include_date=False,
                                indent=None):
    """
    Export parameters of the model to a json file or return a json string.
    :param filepath: Filepath to dump the json string to, or "" to just return the string, or None to return the dict
    :param version: String to include in the "version" field of the json
    :return: Nothing if dumping to json file, or the json string if argument filepath=None
    """
    model_params = get_model_attributes(model,
                                        include,
                                        exclude,
                                        model_name_as_dict_root,
                                        as_is_types
                                        )
    model_params = model_params.copy()

    if include_date:
        model_params['date'] = str(datetime.now())
        if isinstance(include_date, basestring) and include_date == 'as string':
            model_params['date'] = str(model_params['date'])
    if version:
        model_params['version'] = version
    if filepath is not None:
        if filepath == '':
            return dumps(model_params, indent=indent, cls=NumpyAwareJSONEncoder)
        else:
            print("Saving the centroid_model_params to {}".format(filepath))
            dump(model_params, open(filepath, 'w'), indent=indent, cls=NumpyAwareJSONEncoder)
    else:
        return model_params


def import_model_from_spec(spec, objects={}.copy(),
                           type_conversions=(),
                           field_conversions={}.copy(),
                           force_dict_wrap=False):
    if isinstance(spec, dict):
        model_dict_imported = dict()
        for k, v in spec.iteritems():
            if k in objects:
                obj = objects[k]()
                for kk, vv in v.iteritems():
                    setattr(obj, kk,
                            import_model_from_spec(vv, objects, type_conversions, field_conversions, force_dict_wrap))
                model_dict_imported[k] = obj
            elif k in field_conversions:
                v = field_conversions[k](v)
                model_dict_imported[k] = field_conversions[k](v)
            else:
                model_dict_imported[k] = import_model_from_spec(v, objects, type_conversions, field_conversions,
                                                                force_dict_wrap)
        if len(model_dict_imported) == 1 and not force_dict_wrap:
            return model_dict_imported[model_dict_imported.keys()[0]]
        else:
            return model_dict_imported
    else:
        if type_conversions:
            for _type, converter in type_conversions:
                if isinstance(spec, _type):
                    return converter(spec)
        return spec



class NumpyAwareJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            super(self.__class__, self).default(self, obj)
        except TypeError as e:
            if isinstance(obj, np.matrixlib.defmatrix.matrix):
                return list(np.array(obj))
            elif isinstance(obj, np.int32):
                return int(obj)
            else:
                return list(obj)
