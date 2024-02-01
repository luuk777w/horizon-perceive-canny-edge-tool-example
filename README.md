# Creating a gRPC-based Python Application for Edge Detection with OpenCV
 
This guide will walk you through the process of integrating gRPC into a Python application designed for edge detection in images, utilizing the OpenCV library. The application architecture is composed of two main components:

 1. A Python script (canny_edge_detector.py) that performs edge detection on images.
 2. A gRPC server (grpc_server.py) that exposes the edge detection functionality over a gRPC interface.

## Prerequisites
Before we dive into the implementation, ensure you have the following prerequisites installed on your system:

```
 - Python 3.6 or newer
 - OpenCV-Python
 - gRPC and gRPC tools for Python
 - Protocol Buffers (protobuf)
```

You can install the necessary Python packages using pip:

```sh
pip install numpy opencv-python grpcio grpcio-tools
```

## Step 1: Define the gRPC Service and Messages

The foundation of a gRPC service is its interface, defined using Protocol Buffers (protobuf). This definition specifies how clients can interact with your service. For the edge detection application, you need a service that can receive an image, process it to detect edges, and return the processed image.

### The cannyedge.proto File

You start by creating a file named cannyedge.proto. This file contains the definition of the gRPC service and the messages it uses. Here's a breakdown of its contents:

```proto
syntax = "proto3";

service CannyEdgeDetector {
  rpc DetectEdges (stream DetectEdgesRequest) returns (stream DetectEdgesResponse);
}

message DetectEdgesRequest {
  oneof request_data {
    ImageChunk image_chunk = 1;
    Parameters parameters = 2;
  }
}

message ImageChunk {
  bytes content = 1; // Chunk of the image
}

message Parameters {
  int32 minThreshold = 1;
  int32 maxThreshold = 2;
}

message DetectEdgesResponse {
  bytes image_chunk = 1; // Chunk of the processed image
}
```

### Explanation:

 - `syntax = "proto3";` specifies that we are using Protocol Buffers version 3.
 - `service CannyEdgeDetector` defines a service with a single RPC method named `DetectEdges`. This method streams requests and responses, allowing the client to send image data in chunks and receive the processed image in chunks as well.
 - `message DetectEdgesRequest` and `message DetectEdgesResponse` define the request and response types for the `DetectEdges RPC`. The request includes either an image chunk or processing parameters, while the response contains a chunk of the processed image.
 - The `oneof` keyword in `DetectEdgesRequest` message allows sending either an `ImageChunk` or `Parameters` in each request, not both.
 = `message ImageChunk` and `message Parameters` define the structure for sending image data and edge detection parameters, respectively.


> **This guide uses streaming for its requests and responses. This is important as inputs or outputs could be very large. While streaming the input/output adds complexity, it removes the limitations of using buffered requests.**


## Step 2: Generate the gRPC Code

With the `cannyedge.proto` file defined, the next step is to generate the Python code that gRPC uses to serialize, deserialize, and transport your messages over the network. This code generation step creates stubs for the client and server, allowing you to implement the actual logic of your service in Python.

### Generating Python gRPC Code:

Ensure you have the necessary tools installed (grpcio and grpcio-tools). If not, you can install them using pip:

```sh
pip install grpcio grpcio-tools
```

Run the following command in your terminal, in the directory where your cannyedge.proto file is located:

```sh
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. cannyedge.proto
```

This command tells the protobuf compiler to generate Python code (`--python_out`) and gRPC-specific code (`--grpc_python_out`) from your .proto file. `-I.` specifies the directory where your .proto files are located.

### What's Generated:

`cannyedge_pb2.py`: Contains message classes.
`cannyedge_pb2_grpc.py`: Contains server and client classes.
These files are essential for the next steps, where you'll implement the edge detection logic and the gRPC server.

## Step 3: Implement the Python Script for Edge Detection

After defining your gRPC service and generating the necessary Python gRPC code, the next step is to implement the core functionality of your application: edge detection using OpenCV in Python. This will be done in a script named canny_edge_detector.py.

### The canny_edge_detector.py Script
This script performs edge detection on images using the Canny edge detection algorithm provided by OpenCV. It reads image data, applies the edge detection process, and returns the result as a base64-encoded string, suitable for transmission over a network.

```python
import numpy as np
import cv2
import base64

def detect_edges(image_data, min_threshold, max_threshold):
    """
    Detects edges in an image using the Canny edge detection algorithm.

    Args:
        image_data (bytes): The raw image data.
        min_threshold (int): The minimum threshold for the Canny edge detector.
        max_threshold (int): The maximum threshold for the Canny edge detector.

    Returns:
        str: A base64-encoded string of the image with detected edges.
    """

    try:
        # Convert the byte data to a numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        # Decode the numpy array into an image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise Exception("Invalid image data provided") from e

    # Apply the Canny edge detector
    edges = cv2.Canny(image, min_threshold, max_threshold)
    _, buffer = cv2.imencode('.jpg', edges)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    return encoded_image
```

Key Components:

 - **Imports:** The script starts by importing necessary modules. numpy for handling image data as arrays, cv2 (OpenCV) for image processing, and base64 for encoding the processed image.
 - **Function detect_edges:** This function is the heart of the script. It takes raw image data and two threshold values as input. The image data is first converted from a byte array into a format OpenCV can work with, then processed using the Canny edge detection algorithm, and finally encoded as a base64 string.
Understanding the Process
 - **Image Data Conversion:** The raw image data received by the function is in bytes format. This data is converted into a NumPy array, which OpenCV can use to decode the image into a format it can process.
 - **Edge Detection:** The `cv2.Canny()` function applies the Canny edge detection algorithm to the image. The min_threshold and max_threshold parameters are used by the algorithm to identify edges.
 - **Encoding:** The processed image, now containing just the edges, is re-encoded as a JPEG image, converted to a byte array, and then encoded as a base64 string. This string can be easily transmitted over a network.
This script is a standalone component that you'll call from the gRPC server to process images sent by clients.

## Step 4: Implement the gRPC Server
Now that we have the edge detection functionality encapsulated in the `canny_edge_detector.py` script, it's time to set up the gRPC server that will expose this functionality as a service. This server will handle client requests to process images, use the detect_edges function to perform edge detection, and then send the processed images back to the clients.

### The grpc_server.py Script
This script implements the gRPC server, defining how the server handles incoming DetectEdges requests using the service definition from the cannyedge.proto file. We'll break down the server implementation into key parts:

### Import Required Modules
First, import necessary modules and packages, including gRPC-related ones and the auto-generated code from our .proto file, as well as the detect_edges function from canny_edge_detector.py.

```python
from concurrent import futures
import logging
import grpc
import asyncio
from grpc import aio

import base64
import canny_edge_detector

import cannyedge_pb2
import cannyedge_pb2_grpc
```

### Define the Service Implementation
Create a class that inherits from the generated CannyEdgeDetectorServicer class. This class implements the logic for the DetectEdges RPC call.

```python
class CannyEdgeDetector(cannyedge_pb2_grpc.CannyEdgeDetectorServicer):
    async def DetectEdges(self, request_iterator, context):
        min_threshold = max_threshold = None
        image_data = bytearray()

        try:
            async for request in request_iterator:
                if request.HasField("parameters"):
                    min_threshold = request.parameters.minThreshold
                    max_threshold = request.parameters.maxThreshold
                elif request.HasField("image_chunk"):
                    image_data.extend(request.image_chunk.content)

            if min_threshold is not None and max_threshold is not None:
                encoded_image = canny_edge_detector.detect_edges(image_data, min_threshold, max_threshold)
                processed_image = base64.b64decode(encoded_image)
                for i in range(0, len(processed_image), 2048):
                    yield cannyedge_pb2.DetectEdgesResponse(image_chunk=processed_image[i:i + 2048])
            else:
                raise ValueError("Missing image processing parameters")
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Error occurred: {}'.format(str(e)))
```

### Key Components:

- **DetectEdges Method:** This asynchronous method processes incoming requests. It collects image data and parameters from the request stream, performs edge detection, and sends back the processed image in chunks.
- **Error Handling:** Proper error handling is implemented to catch exceptions and set gRPC status codes and messages accordingly.
Set Up and Start the Server

Finally, define a function to configure and start the gRPC server. This includes specifying the server's address, adding the service implementation, and starting the server to listen for incoming requests.

```python
async def serve():
    server = aio.server(futures.ThreadPoolExecutor(max_workers=10))
    cannyedge_pb2_grpc.add_CannyEdgeDetectorServicer_to_server(CannyEdgeDetector(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("Server started, listening on 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig()
    asyncio.run(serve())
```

## Step 5: running the Server:

To run the server, execute the grpc_server.py script. It will start the server and listen on port 50051 for incoming connections.

```sh
python grpc_server.py
```

This server is now capable of receiving image data and parameters from clients, processing the images to detect edges, and streaming back the results.

### Conclusion of Server Setup
You've successfully set up the gRPC server for your edge detection application. This server uses asynchronous processing to handle streaming requests and responses, making it efficient for processing potentially large images in chunks.

In this guide, we've covered defining the gRPC service, generating Python gRPC code, implementing the edge detection functionality, and setting up the server. With these components, you have a complete system that can process images sent by clients, detect edges, and return the processed images.

### Testing the server

The next step would involve creating a client that can connect to this server, send images and parameters for processing, and receive the processed images. This would complete the end-to-end system for edge detection using gRPC and Python.

For this, there is a script available in this repository named `do_request_example.py`. This script acts as a client that connects to the gRPC server, sends an image for edge detection, and handles the streamed response containing the processed image.

## Funding
[<img src="https://github.com/luuk777w/horizon-perceive-backend/assets/22987811/e6667af5-71e3-4845-931f-273cdd6f525b" height="80" align="left" alt="European emblem">](http://ec.europa.eu/)

<br><br><br>

Funded by the European Union's [Horizon Europe research and innovation programme](https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe_en) under [grant agreement Nr. 101061157](https://cordis.europa.eu/project/id/101061157). Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Research Executive Agency (REA). Neither the European Union nor the granting authority can be held responsible for them.
