# Use the official Python base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install custom newspaper package from fork
RUN pip install git+https://github.com/alexcannan/newspaper.git@master

# Copy the source code to the working directory
COPY . .

# Install the application using setup.py
RUN python setup.py install

# Expose the port that the app listens on
EXPOSE 7654

# Start the Uvicorn server
CMD ["uvicorn", "articlesa.serve:app", "--host", "0.0.0.0", "--port", "7654"]