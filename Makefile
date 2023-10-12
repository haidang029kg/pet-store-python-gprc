# Variables
PROTOC = protoc
PROTO_DIR = ./protos
PROTO_FILES = $(wildcard $(PROTO_DIR)/*.proto)
PROTO_OUT_DIR = ./generated

# Targets
.PHONY: grpc-inventory

server:
	python inventory_server.py

build:
	python -m grpc_tools.protoc -I./protos --mypy_out=$(PROTO_OUT_DIR) --python_out=$(PROTO_OUT_DIR) --grpc_python_out=$(PROTO_OUT_DIR) $(PROTO_FILES)

aerich-init:
	aerich init -t settings.TORTOISE_ORM --location models/migrations

db-ssh-tunnel:
	ssh -N -L 5439:localhost:5432 root@hung-vps
