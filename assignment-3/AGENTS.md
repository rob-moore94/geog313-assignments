This project is a simple assignment to compare agentic code and solutions to hand written code. We will be using haversine formula and mathmatical tools to assess distances between cities.

This project uses a pixi environment and includes pixi.toml file to house package dependencies, .gitattributes, .gitignore files to prepare for git repository after completion. Only add a distance.py files to this project to help achieve project goal

Environment and tooling — this project uses pixi; the agent must never suggest pip, conda, or venv; the only third-party dependency allowed is tabulate and testing tool; the agent must not edit the [tasks] section without being asked.

These codes will use the haversine formula on a spherical Earth with a radius of 6371km. Lattitude must be in [-90,90]; longitude should be normalized into [-180,180]; code will report distances between areas in km and miles

Code structure and rules - the core calculation will strictly be numbers in and numbers out so tests can call it back directly. So anything that reads from the terminal lives inside of if __name__ == "__main__":

Definition of done - e.g. pixi run test passes and pixi run distances prints the table