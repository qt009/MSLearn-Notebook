## 1. Setup & Installation

This project uses [uv](https://github.com/astral-sh/uv), an extremely fast Python package and project manager. Follow the steps below to set up your local development environment.

### Prerequisites

First, ensure you have `uv` installed on your machine:

* **macOS/Linux:**
  ```bash
  curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

    ```

* **Windows (PowerShell):**
    ```powershell
    powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

    ```

### Getting Started

1. **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```


2. **Install dependencies and create the virtual environment:**
`uv` handles environment creation and dependency resolution in a single step using the `uv.lock` file:
    ```bash
    uv sync
    ```

    *(This will automatically create a `.venv` folder and install the exact pinned versions of all required packages.)*

3. **Activate the virtual environment:**
    * **macOS/Linux:** `source .venv/bin/activate`
    * **Windows:** `.venv\Scripts\activate`


4. **Verify the installation:**
Ensure FastAPI and Uvicorn are accessible within your environment:
    ```bash
    uvicorn --version
    ```

