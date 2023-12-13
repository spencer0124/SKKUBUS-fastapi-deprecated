from fastapi import FastAPI

app = FastAPI()
a = 3

@app.get("/home/{name}")
def read_name(name:str):
    global a
    a += 1
    return {'name' : name}


@app.get("/home_err/{name}")
def read_name_err(name:int):
    return {'name' : name, 'v': a}

# run app
