# Gems Inventory Management System

This project is a Gems Inventory Management System developed using Flask, a Python web framework. The system provides features for managing gems inventory, filtering and generating reports, and more.

## Features

- User authentication and authorization
- Inventory management: add, edit, and delete gems
- Filtering inventory based on type and price range
- Generating PDF reports using `wkhtmltopdf`
- Responsive design for mobile and desktop views

## Technologies Used

- Python
- Flask
- Flask-Login
- SQLAlchemy
- Jinja2
- Bootstrap
- jQuery
- wkhtmltopdf

## Installation

### Prerequisites

- Python 3.x
- `wkhtmltopdf` installed and available in your system PATH

### Step-by-Step Guide

1. **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/gems-inventory-management.git
    cd gems-inventory-management
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the database:**
    ```sh
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

5. **Run the application:**
    ```sh
    flask run
    ```

### Automated Installation of `wkhtmltopdf` for Windows


1. **Run the batch file before starting the application:**
    ```sh
    install_wkhtmltopdf.bat
    ```

## Usage

- Navigate to the home page and log in using your credentials.
- Use the navigation bar to access different sections of the system.
- Add, edit, or delete gems in the inventory.
- Use the filter options to refine your search.
- Generate PDF reports for the selected date range.

## Contributing

If you would like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, please contact [nilupulpathum2004@gmail.com](mailto:nilupulpathum2004@gmail.com).
