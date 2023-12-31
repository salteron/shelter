# SHELTER

Проект является решением тестового задания, сформулированного в [TASK.md](./TASK.md).

Задание понял следующим образом 
- пользователь может вывести деньги с кошелька только на ту платежную систему и
  на тот счет, с которых этот кошелек был пополнен
- платежная система не берет комиссию

В результате переговоров с командой Superpay:
- Superpay предоставляет как боевую, так и тестовую площадки;
- АПИ Superpay переезжает с http на https для повышения безопасности;
- аутентификация в АПИ Superpay реализуется по схеме Basic Authentication, где в
  качестве username / password используются client-id / client-secret;
- АПИ Superpay позволяет сопровождать запросы ключом идемпотентности, указывая
  его в заголовке X-Idempotency-Key. Это защитит нас от дублирующихся
  транзакций;
- транзакции (депозит, выплата) на стороне Superpay создаются в статусе pending,
  затем приобретают один из двух конечных статусов - succeeded или canceled;
- метод создания депозита возвращает ссылку для подтверждения, ведущую на
  страницу оплаты на сайте Superpay;
- если в течение времени t пользователь не перешел по ссылке и не произвел
  оплату, то Superpay переводит такие депозиты в статус canceled;
- Superpay уведомляет нас о смене статуса каждой транзакции отдельным POST
  запросом на колбек /payment-systems/superpay/callback;
- ответ 200 с нашей стороны означает, что событие успешно обработано. В случае
  другого статуса ответа Superpay продолжит периодически уведомлять о данном
  событии в течение N дней;
- отправляя запросы на колбек, Superpay прикладывает подпись их содержимого для
  того, чтобы мы могли убедиться, что запрос поступил именно от них (подробнее в
  superpay.py).

На данный момент точкой входа в сценарий создания депозита является 
`shelter/transactions/services.py::create_deposit`

На данный момент точкой входа в сценарий создания выплаты является 
`shelter/transactions/services.py::create_payout`

## Requirements

- [docker](https://www.docker.io/)
- [docker-compose](https://docs.docker.com/compose/)

## Run tests

`$ make compose-test`
