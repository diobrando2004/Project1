from deepface import DeepFace

def verify_faces(img1_path, img2_path):
    try:
        result = DeepFace.verify(img1_path=img1_path, img2_path=img2_path)
        if result['verified']:
            print("Faces match!")
        else:
            print("Faces do not match.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Paths to the images
    img1_path = "Johnny1.jpg"
    img2_path = "henry1.jpg"

    verify_faces(img1_path, img2_path)
