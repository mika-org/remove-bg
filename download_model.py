import rembg

def main():
    print("Pre-downloading default U-2-Net model for rembg...")
    # Creating a session triggers downloading the model if not present.
    try:
        rembg.new_session()
        print("Success: Model has been downloaded and cached successfully!")
    except Exception as e:
        print(f"Error downloading model: {e}")
        raise e

if __name__ == "__main__":
    main()
