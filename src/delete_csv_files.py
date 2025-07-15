import os
import glob

# Supprimer tous les fichiers .csv dans le répertoire courant
def delete_csv_files():
    for file in glob.glob("*.csv"):
        try:
            os.remove(file)
            print(f"✅ Supprimé : {file}")
        except Exception as e:
            print(f"❌ Erreur suppression {file} : {e}")