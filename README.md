# PPE Detection System

This project provides a comprehensive solution for Personal Protective Equipment (PPE) detection, leveraging advanced computer vision techniques, specifically YOLOv8. It includes a user-friendly web interface for image upload, real-time webcam detection, and a gallery of processed images, making it suitable for various industrial and safety monitoring applications.

## Features

- **Real-time PPE Detection**: Instantly identify safety gear like helmets, vests, and gloves using live camera feeds.
- **Image Upload & Processing**: Upload images for PPE detection and visualize the results with bounding boxes and labels.
- **Interactive Gallery**: Browse and manage previously processed images, viewing both original and detected versions.
- **Responsive Web Interface**: A modern and intuitive UI/UX built with Django and Tailwind CSS, ensuring accessibility across devices.
- **Dark Mode Support**: Seamlessly switch between light and dark themes for enhanced viewing comfort.
- **Robust Error Handling**: Comprehensive client-side and server-side validation for file uploads and processing.
- **Easy Setup**: Simple steps to get the project up and running in a virtual environment.

## Demo

Check out a live demo of the project [here](https://ppe-django.onrender.com) .

## Setup

Follow these steps to set up the project locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ppe-detection.git
    cd ppe-detection
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv env
    ```

3.  **Activate the virtual environment:**
    -   **On Linux/macOS:**
        ```bash
        source env/bin/activate
        ```
    -   **On Windows:**
        ```bash
        .\env\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

    The web application will be accessible at `http://127.0.0.1:8000/`.

## Project Structure

-   `manage.py`: Django's command-line utility for administrative tasks.
-   `requirements.txt`: Lists all Python dependencies.
-   `data.yaml`: Configuration file for YOLOv8 (e.g., dataset paths, class names).
-   `ppe_rinl.ipynb`: Jupyter notebook for initial analysis, model training, or detailed experimentation.
-   `yolov8n.pt`: Pre-trained YOLOv8 model weights (or your fine-tuned model).
-   `demo/`:
    -   `demo/settings.py`: Django project settings.
    -   `demo/urls.py`: Main URL routing for the Django project.
    -   `myapp/`: Django application containing core logic.
        -   `myapp/views.py`: Handles web requests and rendering of pages.
        -   `myapp/models.py`: Database models for uploaded images.
        -   `myapp/urls.py`: URL patterns for the `myapp` application.
        -   `myapp/templates/myapp/`: HTML templates for UI rendering.
        -   `myapp/static/`: Static assets like CSS, JS, and images (though much is handled by Tailwind CDN).
-   `env/`: Python virtual environment (not to be committed to Git).
-   `runs/`: Directory for YOLOv8 training and detection outputs.

## Usage

Once the development server is running, navigate to `http://127.0.0.1:8000/` in your web browser.

-   **Home**: The landing page provides an overview of the system's capabilities.
-   **Upload**: Upload an image (JPG, PNG, WebP) for PPE detection. The processed image will be displayed along with detection results.
-   **Gallery**: View a collection of all previously uploaded and processed images.
-   **Webcam**: Access live PPE detection using your webcam (requires a compatible browser and camera setup).
-   **Dark Mode**: Toggle between light and dark themes using the button in the navigation bar.

## Contributing

We welcome contributions to enhance this project! To contribute:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'feat: Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request, describing your changes in detail.

Please ensure your code adheres to the existing style and conventions.

## License

This project is open-source and available under the [MIT License](LICENSE). 