import os
import rembg

def main():
    # Set U2NET_HOME to .u2net folder inside the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    u2net_home = os.path.join(current_dir, ".u2net")
    os.environ["U2NET_HOME"] = u2net_home
    os.makedirs(u2net_home, exist_ok=True)

    print(f"Pre-downloading lightweight u2netp model for rembg to {u2net_home}...")
    try:
        rembg.new_session("u2netp")
        print("Success: u2netp model has been downloaded and cached successfully!")
    except Exception as e:
        print(f"Error downloading model: {e}")
        raise e

if __name__ == "__main__":
    main()
