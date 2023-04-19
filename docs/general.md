# SETUP
## DB-SETUP
```bash
docker run -d --name sailfish_dev -e POSTGRES_USER=root -e POSTGRES_PASSWORD=root -e POSTGRES_DB=sailfish_dev -p 5432:5432 postgres:13
```
