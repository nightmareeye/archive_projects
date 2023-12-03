Сначала выполнить (ОДИН РАЗ!):

	docker volume create database

Создание Docker-образа:
Выполните следующую команду в той же директории, что и проект:

	docker build -t mphelp_bot .

Запуск контейнера:
Замените bot_container_name на имя для вашего контейнера.

	docker run -v database:/data --restart unless-stopped --name bot_containter_name mphelp_bot

Остановка контейнера:
Чтобы остановить контейнер, выполните:

	docker stop bot_container_name

Запуск контейнера:

	docker start bot_container_name