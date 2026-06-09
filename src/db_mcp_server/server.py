from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-world")


@mcp.tool()
def hello(name: str = "world") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
