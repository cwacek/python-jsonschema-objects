import pytest

import python_jsonschema_objects as pjo
import python_jsonschema_objects.util as util
from python_jsonschema_objects.classbuilder import ProtocolBase

def test_name_conflict_literal_class():
    schema = {
        'title': 'name conflict',
        'type': 'object',
        'definitions': {
          "Path": {
            "title": "Path", 
            "type": "object", 
            "additionalProperties": False, 
            "properties": {
              "path": {
                "type": "string", 
              },
              "parent": {
                  "$ref": "#/definitions/Path"
              }
            }
          }
        }
    }
    builder = pjo.ObjectBuilder(schema)
    klasses = builder.build_classes()
    p = klasses.Path
    # without correction, returned class is #/definitions/Path/path which is a literal
    assert util.safe_issubclass(p, ProtocolBase)

test_name_conflict_literal_class()