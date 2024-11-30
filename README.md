# HAS (Household-Services-App)

## Overview

The Household Services Application (HSA) is a multi-user platform designed to connect customers with service professionals for various household services. The platform enables customers to browse available services, request appointments, and view their service history, while service professionals can manage incoming requests. The admin has complete oversight of user accounts, service offerings, and request statuses.

## Features

### For Admin:
- **Dashboard:** Provides an overview of platform activity, including user statistics, service requests, and system metrics.
- **User Management:** Add, edit, or remove user accounts (customers and service professionals).
- **Service Management:** Create, update, and manage all services offered on the platform.
- **Request Management:** View and oversee all service requests, manage request statuses, and assign professionals to requests if necessary.

### For Service Professionals:
- **Dashboard:** Shows an overview of assigned service requests, including pending and completed services.
- **Request Management:** View and update the status of service requests (e.g., "In Progress," "Completed").
- **Availability Management:** Update personal availability to ensure accurate scheduling.

### For Customers:
- **Dashboard:** Displays an overview of booked services, pending requests, and service history.
- **Service Request:** Browse available services, select preferred professionals (if applicable), and book services.
- **Request Tracking:** Monitor the status of service requests and receive notifications upon completion.
- **Service History:** View past services for reference or rebooking.

## Technologies Used
- **Flask**: Python web framework for backend logic.
- **Bootstrap**: Frontend framework for styling and responsive design.
- **SQLite**: Database for data persistence.
- **Jinja2**: Templating engine for rendering HTML with dynamic data.

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- Flask and other required dependencies (specified in `requirements.txt`)

### Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/22f3001041/Household-Services-App-V1
   cd HSA
   ```

2. **Install dependencies:**
   ```
    pip install -r requirements.txt
    ```
3. **Run the application:**
    ```
    python app.py
    ```
The app will be accessible at https://127.0.0.1:5000/. The database will be created automatically on first run.

## File Structure
```
HSA/
│
├── static/
│   └──style.css              # Custom styles
├── templates/                # HTML templates for rendering pages
├── app.py                    # Main application file
├── config.py                 # Configuration file
├── README.md                 # Project documentation
├── requirements.txt          # Project dependencies
```
