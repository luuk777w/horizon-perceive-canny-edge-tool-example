import grpc
import cv2
import numpy as np
import matplotlib.pyplot as plt
from tkinter import filedialog
from tkinter import Tk
import cannyedge_pb2_grpc
import cannyedge_pb2
import asyncio

# Function to display image
def display_image(image, title="Image"):
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title(title)
    plt.axis('off')
    plt.show()

def generate_requests(image_path):
    # Send parameters first
    yield cannyedge_pb2.DetectEdgesRequest(
        parameters=cannyedge_pb2.Parameters(minThreshold=100, maxThreshold=200)
    )

    # Then send the image in chunks
    chunk_size = 2048  # Define the size of each chunk
    with open(image_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield cannyedge_pb2.DetectEdgesRequest(
                image_chunk=cannyedge_pb2.ImageChunk(content=chunk)
            )

async def process_image(image_path):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = cannyedge_pb2_grpc.CannyEdgeDetectorStub(channel)

        # Create a synchronous request iterator
        request_iterator = generate_requests(image_path)
        response_iterator = stub.DetectEdges(request_iterator)
        
        # Receive and assemble the processed image chunks
        processed_image_data = bytearray()
        for response in response_iterator:
            processed_image_data.extend(response.image_chunk)

        # Convert the processed image data to an image
        processed_image = np.frombuffer(processed_image_data, dtype=np.uint8)
        processed_image = cv2.imdecode(processed_image, cv2.IMREAD_COLOR)

        # Display the processed image
        display_image(processed_image, "Processed Image")

# Prompt user to select an image
root = Tk()
root.withdraw()  # Hide the main window
image_path = filedialog.askopenfilename(title='Select an image')
root.destroy()

# Load and display the selected image
original_image = cv2.imread(image_path)
display_image(original_image, "Original Image")

# Process the image
asyncio.run(process_image(image_path))
