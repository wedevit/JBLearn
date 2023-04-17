find . -path "*migrations*" -not -regex ".*__init__.py" -a -not -regex ".*migrations" | xargs rm -rf
rm -rf db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata languages.json submissions.json