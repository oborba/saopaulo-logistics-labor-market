# 🚚 São Paulo Professional Drivers Analysis

This application analyzes open data provided by Detran-SP, the governmental agency responsible for issuing and regulating driver's licenses in São Paulo, Brazil.

The dashboard provides insights into the distribution of drivers qualified for commercial vehicles (trucks, buses, and heavy-duty vehicles). This dataset represents the "Professional Drivers" segment, which is the backbone of the state's logistics sector.

## 🛠️ Tech Stack

**Framework**: Streamlit

**Python Libs**: E.g: Pandas, Plotly

**Environment Management**: Conda / Pip

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.


- **Python** 3.12

- **Conda** (optional, but recommended)

### Installation
- Create a virtual environment:

`$ conda create -n sp-logistics python=3.12`

- Activate the environment:

`$ conda activate sp-logistics`

- Install the dependencies:

`$ pip install -r requirements.txt`

- Run the application:

`$ streamlit run streamlit_app.py`

**Note**: The analysis is based on the ```condutores_habilitados_ativos_incrementado.csv``` file, which serves as our local data source.