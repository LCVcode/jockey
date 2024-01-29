from jockey.jockey import convert_object_abbreviation, ObjectType


def test_object_type_retrieval():
    """Test that object type retrieval works with abbreviations."""

    for obj_type in ObjectType:
        for abbrev in obj_type.value:
            assert convert_object_abbreviation(abbrev) == obj_type

    for abbrev in ("b", "d", "e", "f", "machine_id"):
        assert convert_object_abbreviation(abbrev) == None
