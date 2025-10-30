from dotenv import load_dotenv
import os

def check_maintance():

    load_dotenv()  # This will load variables from the .env file
    manutencao = os.getenv("MANUTENCAO")
    if manutencao == "true":
        print("Manutenção")
        breakpoint()