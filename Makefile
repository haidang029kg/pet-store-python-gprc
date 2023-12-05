# Variables
PROTOC = protoc
PROTO_DIR = ./protos
PROTO_FILES = $(wildcard $(PROTO_DIR)/*.proto)
PROTO_OUT_DIR = ./generated

# Targets
.PHONY: server gen-code aerich-init db-ssh-tunnel clean help

server:
	python server_grpc.py

# Generate the gRPC code
gen-code:
	python -m grpc_tools.protoc -I./protos --mypy_out=$(PROTO_OUT_DIR) --python_out=$(PROTO_OUT_DIR) --grpc_python_out=$(PROTO_OUT_DIR) $(PROTO_FILES)

# Initialize Aerich for database migrations
aerich-init:
	aerich init -t settings.TORTOISE_ORM --location models/migrations

# Create an SSH tunnel to the database
db-ssh-tunnel:
	ssh -N -L 5439:localhost:5432 root@hung-vps

# Remove the generated code
clean:
	rm -rf $(PROTO_OUT_DIR)/*

# Display this help message
help:
	@echo "Available targets:"
	@echo "  server       - Start the grpc server"
	@echo "  gen-code     - Generate the gRPC code"
	@echo "  aerich-init  - Initialize Aerich for database migrations"
	@echo "  db-ssh-tunnel - Create an SSH tunnel to the database"
	@echo "  clean        - Remove the generated code"
