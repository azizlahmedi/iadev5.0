# Utilisez l'image officielle de Python comme image de base
FROM python:3.8-slim-buster

# Configurez le répertoire de travail pour le conteneur
WORKDIR /app

# Copiez les fichiers requirements.txt et votre code source dans le conteneur
COPY requirements.txt .
COPY . .

# Installez les dépendances Python requises
RUN pip install --no-cache-dir -r requirements.txt

# Exposez le port 8050 pour que le serveur web puisse être accessible depuis l'extérieur du conteneur
EXPOSE 8050

# Définissez les variables d'environnement pour le projet Django
ENV DJANGO_SETTINGS_MODULE=django_project.settings
ENV PYTHONPATH=/app

# Démarrez le serveur web Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8050"]
