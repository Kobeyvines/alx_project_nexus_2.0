# use official python image
FROM python:3.11


# set work directory
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


#Copy project files
COPY . .

#Expose port
EXPOSE 8000

#Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


