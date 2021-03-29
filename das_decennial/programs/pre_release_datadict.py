from constants import CC
import programs.constraints.Constraints_DHCP_HHGQ as Constraints_DHCP_HHGQ
import programs.constraints.Constraints_Household2010 as Constraints_Household2010



# def getSchema(schema_name: str) -> programs.schema.schema:
#     """
#     returns the Schema object from the schema module associated with schema_name
#
#     Inputs:
#         schema_name (str): the name of the schema class desired
#
#     Outputs:
#         a Schema object
#     """
#     schema = SchemaMaker.fromName(schema_name)
#     return schema


def getConstraintsModule(schema_name):
    """
    returns the constraints module associated with the schema_name
    
    Inputs:
        schema_name (str): the name of the schema class desired
    
    Outputs:
        a constraints module
    """
    constraint_modules = {
        CC.DAS_DHCP_HHGQ: Constraints_DHCP_HHGQ,
        CC.DAS_Household2010: Constraints_Household2010,
    }
    assert schema_name in constraint_modules, f"The '{schema_name}' constraint module can't be found."
    return constraint_modules[schema_name]
