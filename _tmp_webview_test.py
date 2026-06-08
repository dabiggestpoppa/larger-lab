import webview
import sys

print("pywebview loaded OK")
print("Python version:", sys.version)

# Try to create a simple test window
try:
    window = webview.create_window(
        title="Test",
        url="http://localhost:12393",
        width=400,
        height=300,
    )
    print("Window created OK")
    webview.start(debug=True)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
