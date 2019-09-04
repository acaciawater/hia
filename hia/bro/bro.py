# import xmlschema
# from xmlschema.validators.exceptions import XMLSchemaValidationError
# 
# GOED = r'/home/theo/src/bro/bro/Test_molenlanden_B38D4887_D03.xml'
# FOUT = r'/home/theo/src/bro/bro/Test_molenlanden_B38D4887_D03_fout.xml'
# schema = r'/home/theo/src/bro/bro/isgmw_messages.xsd'
# document = FOUT
# 
# def main():
#     try:
#         xmlschema.validate(document, schema)
#         print('{} is valid'.format(document))
#     except XMLSchemaValidationError as error:
#         print('Invalid document\n{}\nLocation: {}\nReason: {}\n'.format(
#             error.message,
#             error.path,
#             error.reason))
# 
# if __name__ == '__main__':
#     main()
