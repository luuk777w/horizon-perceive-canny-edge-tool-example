from concurrent import futures
import logging

# Importing necessary modules and protobuf definitions for gRPC
import base64
import canny_edge_detector
import grpc
import cannyedge_pb2
import cannyedge_pb2_grpc
from grpc import aio 
import asyncio

class CannyEdgeDetector(cannyedge_pb2_grpc.CannyEdgeDetectorServicer):
    """
    This class defines the server-side implementation of the gRPC service.
    It inherits from the auto-generated class from protobuf which defines the server-side view of the gRPC methods.
    """

    async def DetectEdges(self, request_iterator, context):
        """
        Server-side implementation of the DetectEdges gRPC method.

        Args:
            request: The client's request message, containing the image data and edge detection parameters.
            context: Contextual information about the RPC (Remote Procedure Call).

        Returns:
            A DetectEdgesResponse message containing the processed image.
        """
        min_threshold = max_threshold = None
        image_data = bytearray()

        try:
            async for request in request_iterator:
                
                if request.HasField("parameters"):
                    # First message should contain the parameters
                    min_threshold = request.parameters.minThreshold
                    max_threshold = request.parameters.maxThreshold
                elif request.HasField("image_chunk"):
                    # Subsequent messages will contain the image chunks
                    image_data.extend(request.image_chunk.content)
            print("5")
            if min_threshold is not None and max_threshold is not None:
                # Process the image and get the result as a base64 string
                base64_encoded_image = canny_edge_detector.detect_edges(image_data, min_threshold, max_threshold)
                
                # Decode the base64 string to bytes
                processed_image = base64.b64decode(base64_encoded_image)
                
                # Send the processed image in chunks
                for i in range(0, len(processed_image), 2048): # Adjust chunk size as needed
                    yield cannyedge_pb2.DetectEdgesResponse(image_chunk=processed_image[i:i + 2048])

            else:
                raise ValueError("Missing image processing parameters")
        except Exception as e:
            # If an error occurs, map the Python exception to a gRPC status code and return an empty response
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Error occurred: {}'.format(str(e)))
            return  # Return an empty response in case of error
        
async def serve():
    """
    This function sets up and starts the gRPC server.
    """

    # Create a gRPC server with a thread pool executor for handling incoming requests
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the defined CannyEdgeDetector service to the server
    cannyedge_pb2_grpc.add_CannyEdgeDetectorServicer_to_server(CannyEdgeDetector(), server)
    
    # Specify the port for the server to listen on and start the server
    server.add_insecure_port("[::]:50051")
    await server.start()
    
    # Print a message indicating the server has started and is listening for requests
    print("Server started, listening on 50051")

    # Keep the server running indefinitely to listen for incoming requests
    await server.wait_for_termination()

if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig()
    # Start the server by calling the serve function
    asyncio.run(serve())
