# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: inventory.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0finventory.proto\x12\tinventory\x1a\x1fgoogle/protobuf/timestamp.proto\"k\n\x0cPurchaseItem\x12\x12\n\nproduct_id\x18\x01 \x01(\t\x12\x0b\n\x03sku\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\r\n\x05price\x18\x04 \x01(\x05\x12\x19\n\x11unique_identifier\x18\x05 \x01(\t\"\xba\x01\n\x0bPurchaseRes\x12+\n\x07\x63reated\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12,\n\x08modified\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x13\n\x0btotal_units\x18\x03 \x01(\x05\x12\x13\n\x0btotal_price\x18\x04 \x01(\x03\x12&\n\x05items\x18\x05 \x03(\x0b\x32\x17.inventory.PurchaseItem\"I\n\x11\x43reatePurchaseReq\x12\x0c\n\x04note\x18\x01 \x01(\t\x12&\n\x05items\x18\x02 \x03(\x0b\x32\x17.inventory.PurchaseItem\"2\n\x0eGetQuantityReq\x12\x12\n\nproduct_id\x18\x01 \x01(\t\x12\x0c\n\x04skus\x18\x02 \x03(\t\"B\n\rQuantityBySku\x12\x12\n\nproduct_id\x18\x01 \x01(\t\x12\x0b\n\x03sku\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\";\n\x0eGetQuantityRes\x12)\n\x07results\x18\x01 \x03(\x0b\x32\x18.inventory.QuantityBySku\"l\n\rSaleOrderItem\x12\x12\n\nproduct_id\x18\x01 \x01(\t\x12\x0b\n\x03sku\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\r\n\x05price\x18\x04 \x01(\x03\x12\x19\n\x11unique_identifier\x18\x05 \x01(\t\"K\n\x12\x43reateSaleOrderReq\x12\x0c\n\x04note\x18\x01 \x01(\t\x12\'\n\x05items\x18\x02 \x03(\x0b\x32\x18.inventory.SaleOrderItem\"\xca\x01\n\x0cSaleOrderRes\x12\x0c\n\x04note\x18\x01 \x01(\t\x12+\n\x07\x63reated\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12,\n\x08modified\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x13\n\x0btotal_units\x18\x04 \x01(\x05\x12\x13\n\x0btotal_price\x18\x05 \x01(\x03\x12\'\n\x05items\x18\x06 \x03(\x0b\x32\x18.inventory.SaleOrderItem2\xea\x01\n\x10InventoryService\x12\x46\n\x0e\x43reatePurchase\x12\x1c.inventory.CreatePurchaseReq\x1a\x16.inventory.PurchaseRes\x12\x43\n\x0bGetQuantity\x12\x19.inventory.GetQuantityReq\x1a\x19.inventory.GetQuantityRes\x12I\n\x0f\x43reateSaleOrder\x12\x1d.inventory.CreateSaleOrderReq\x1a\x17.inventory.SaleOrderResb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'inventory_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _globals['_PURCHASEITEM']._serialized_start=63
  _globals['_PURCHASEITEM']._serialized_end=170
  _globals['_PURCHASERES']._serialized_start=173
  _globals['_PURCHASERES']._serialized_end=359
  _globals['_CREATEPURCHASEREQ']._serialized_start=361
  _globals['_CREATEPURCHASEREQ']._serialized_end=434
  _globals['_GETQUANTITYREQ']._serialized_start=436
  _globals['_GETQUANTITYREQ']._serialized_end=486
  _globals['_QUANTITYBYSKU']._serialized_start=488
  _globals['_QUANTITYBYSKU']._serialized_end=554
  _globals['_GETQUANTITYRES']._serialized_start=556
  _globals['_GETQUANTITYRES']._serialized_end=615
  _globals['_SALEORDERITEM']._serialized_start=617
  _globals['_SALEORDERITEM']._serialized_end=725
  _globals['_CREATESALEORDERREQ']._serialized_start=727
  _globals['_CREATESALEORDERREQ']._serialized_end=802
  _globals['_SALEORDERRES']._serialized_start=805
  _globals['_SALEORDERRES']._serialized_end=1007
  _globals['_INVENTORYSERVICE']._serialized_start=1010
  _globals['_INVENTORYSERVICE']._serialized_end=1244
# @@protoc_insertion_point(module_scope)
