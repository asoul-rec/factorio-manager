# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from grpc_server import server_pb2 as grpc__server_dot_server__pb2


class ServerManagerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetManagerStatus = channel.unary_unary(
                '/factorio_server.ServerManager/GetManagerStatus',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.ManagerStat.FromString,
                )
        self.GetAllSaveName = channel.unary_unary(
                '/factorio_server.ServerManager/GetAllSaveName',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.SaveNameList.FromString,
                )
        self.GetStatByName = channel.unary_unary(
                '/factorio_server.ServerManager/GetStatByName',
                request_serializer=grpc__server_dot_server__pb2.SaveName.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.SaveStat.FromString,
                )
        self.StopServer = channel.unary_unary(
                '/factorio_server.ServerManager/StopServer',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.Status.FromString,
                )
        self.StartServerByName = channel.unary_unary(
                '/factorio_server.ServerManager/StartServerByName',
                request_serializer=grpc__server_dot_server__pb2.ServerOptions.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.Status.FromString,
                )
        self.RestartServer = channel.unary_unary(
                '/factorio_server.ServerManager/RestartServer',
                request_serializer=grpc__server_dot_server__pb2.ServerOptions.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.Status.FromString,
                )
        self.InGameCommand = channel.unary_unary(
                '/factorio_server.ServerManager/InGameCommand',
                request_serializer=grpc__server_dot_server__pb2.Command.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.Status.FromString,
                )
        self.WaitForUpdates = channel.unary_unary(
                '/factorio_server.ServerManager/WaitForUpdates',
                request_serializer=grpc__server_dot_server__pb2.UpdateInquiry.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.GameUpdates.FromString,
                )
        self.GetOutputStreams = channel.unary_unary(
                '/factorio_server.ServerManager/GetOutputStreams',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.OutputStreams.FromString,
                )
        self.UploadToTelegram = channel.unary_stream(
                '/factorio_server.ServerManager/UploadToTelegram',
                request_serializer=grpc__server_dot_server__pb2.UploadTelegramInfo.SerializeToString,
                response_deserializer=grpc__server_dot_server__pb2.Status.FromString,
                )


class ServerManagerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetManagerStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllSaveName(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetStatByName(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartServerByName(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RestartServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InGameCommand(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def WaitForUpdates(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetOutputStreams(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UploadToTelegram(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ServerManagerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetManagerStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.GetManagerStatus,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=grpc__server_dot_server__pb2.ManagerStat.SerializeToString,
            ),
            'GetAllSaveName': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllSaveName,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=grpc__server_dot_server__pb2.SaveNameList.SerializeToString,
            ),
            'GetStatByName': grpc.unary_unary_rpc_method_handler(
                    servicer.GetStatByName,
                    request_deserializer=grpc__server_dot_server__pb2.SaveName.FromString,
                    response_serializer=grpc__server_dot_server__pb2.SaveStat.SerializeToString,
            ),
            'StopServer': grpc.unary_unary_rpc_method_handler(
                    servicer.StopServer,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=grpc__server_dot_server__pb2.Status.SerializeToString,
            ),
            'StartServerByName': grpc.unary_unary_rpc_method_handler(
                    servicer.StartServerByName,
                    request_deserializer=grpc__server_dot_server__pb2.ServerOptions.FromString,
                    response_serializer=grpc__server_dot_server__pb2.Status.SerializeToString,
            ),
            'RestartServer': grpc.unary_unary_rpc_method_handler(
                    servicer.RestartServer,
                    request_deserializer=grpc__server_dot_server__pb2.ServerOptions.FromString,
                    response_serializer=grpc__server_dot_server__pb2.Status.SerializeToString,
            ),
            'InGameCommand': grpc.unary_unary_rpc_method_handler(
                    servicer.InGameCommand,
                    request_deserializer=grpc__server_dot_server__pb2.Command.FromString,
                    response_serializer=grpc__server_dot_server__pb2.Status.SerializeToString,
            ),
            'WaitForUpdates': grpc.unary_unary_rpc_method_handler(
                    servicer.WaitForUpdates,
                    request_deserializer=grpc__server_dot_server__pb2.UpdateInquiry.FromString,
                    response_serializer=grpc__server_dot_server__pb2.GameUpdates.SerializeToString,
            ),
            'GetOutputStreams': grpc.unary_unary_rpc_method_handler(
                    servicer.GetOutputStreams,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=grpc__server_dot_server__pb2.OutputStreams.SerializeToString,
            ),
            'UploadToTelegram': grpc.unary_stream_rpc_method_handler(
                    servicer.UploadToTelegram,
                    request_deserializer=grpc__server_dot_server__pb2.UploadTelegramInfo.FromString,
                    response_serializer=grpc__server_dot_server__pb2.Status.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'factorio_server.ServerManager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ServerManager(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetManagerStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/GetManagerStatus',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            grpc__server_dot_server__pb2.ManagerStat.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllSaveName(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/GetAllSaveName',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            grpc__server_dot_server__pb2.SaveNameList.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetStatByName(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/GetStatByName',
            grpc__server_dot_server__pb2.SaveName.SerializeToString,
            grpc__server_dot_server__pb2.SaveStat.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StopServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/StopServer',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            grpc__server_dot_server__pb2.Status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StartServerByName(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/StartServerByName',
            grpc__server_dot_server__pb2.ServerOptions.SerializeToString,
            grpc__server_dot_server__pb2.Status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RestartServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/RestartServer',
            grpc__server_dot_server__pb2.ServerOptions.SerializeToString,
            grpc__server_dot_server__pb2.Status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InGameCommand(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/InGameCommand',
            grpc__server_dot_server__pb2.Command.SerializeToString,
            grpc__server_dot_server__pb2.Status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def WaitForUpdates(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/WaitForUpdates',
            grpc__server_dot_server__pb2.UpdateInquiry.SerializeToString,
            grpc__server_dot_server__pb2.GameUpdates.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetOutputStreams(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/factorio_server.ServerManager/GetOutputStreams',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            grpc__server_dot_server__pb2.OutputStreams.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UploadToTelegram(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/factorio_server.ServerManager/UploadToTelegram',
            grpc__server_dot_server__pb2.UploadTelegramInfo.SerializeToString,
            grpc__server_dot_server__pb2.Status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
