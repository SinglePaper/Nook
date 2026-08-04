# Nook: A Digital Library for Friends
<img src="nook.png" alt="Nook website front page with several books displayed." width="70%">

Nook is a self-hosted website where you can share your book collection with friends! Look at what other people recommend and see what books you can borrow from them.

To set up your instance of Nook, use the provided venv or ensure the following Python libraries are installed in your environment:
- django
- django-taggit
- djangorestframework

Once your environment is set up, run the following commands in the repository directory:\
<code>python3 manage.py migrate</code>

This will set up your instance of the project. Afterward, run the following command to start the server:\
<code>python3 manage.py runserver 0.0.0.0:8080</code>
