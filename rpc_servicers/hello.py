from generated import hello_pb2, hello_pb2_grpc


class HelloServicer(hello_pb2_grpc.HelloServiceServicer):
    async def SayHello(self, request: hello_pb2.SayHelloReq, context):
        return hello_pb2.SayHelloRes(speech=f"Hello {request.speech}")
