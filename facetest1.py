import json
from deepface import DeepFace
from scipy.spatial.distance import cosine


def save_face_embedding(image_path, embedding_file, model_name="VGG-Face"):
    try:
        embedding = DeepFace.represent(img_path=image_path, model_name=model_name)
        
        with open(embedding_file, "w") as f:
            json.dump(embedding, f)
        
        print(f"Face embedding saved securely to {embedding_file}")
    except Exception as e:
        print(f"Error generating embedding for {image_path}: {e}")

def compare_embeddings(embedding1, embedding2, threshold=0.4):
    try:
        similarity = 1 - cosine(embedding1[0]["embedding"], embedding2[0]["embedding"])
        print(f"Similarity score: {similarity}")
        
        if similarity > threshold:
            print("Faces match!")
        else:
            print("Faces do not match.")
    except Exception as e:
        print(f"Error during comparison: {e}")

if __name__ == "__main__":
    original_image = "henry.jpg"
    new_image = "henry1.jpg"
    original_embedding_file = "henry.json"
    new_embedding_file = "Johnny1.json"
    
    print("Saving embeddings for the original image...")
    save_face_embedding(original_image, original_embedding_file)
    
    print("Saving embeddings for the new image...")
    save_face_embedding(new_image, new_embedding_file)

    try:
        with open(original_embedding_file, "r") as f:
            original_embedding = json.load(f)
        
        with open(new_embedding_file, "r") as f:
            new_embedding = json.load(f)

        print("Comparing the embeddings...")
        compare_embeddings(original_embedding, new_embedding)
    
    except Exception as e:
        print(f"Error loading embeddings: {e}")
