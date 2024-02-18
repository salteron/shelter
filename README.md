# SHELTER

The project is a solution to the test task formulated in [TASK.md](./TASK.md).

I understand the task as follows:
- The user can withdraw money from the wallet only to the payment system and
  to the account from which this wallet was replenished
- The payment system does not charge a commission

As a result of negotiations with the Superpay team:
- Superpay provides both production and test environments
- Superpay's API moves from http to https for increased security
- Authentication in Superpay's API is implemented using the Basic Authentication scheme, where
  client-id / client-secret are used as username / password
- Superpay's API allows accompanying requests with an idempotency key by specifying
  it in the X-Idempotency-Key header. This will protect us from duplicate
  transactions
- Transactions (deposit, payout) on the Superpay side are created in a pending status,
  then they acquire one of two final statuses - succeeded or canceled
- The method of creating a deposit returns a confirmation link leading to
  the payment page on the Superpay website
- If the user does not follow the link and make
  payment within time t, Superpay converts such deposits to canceled status
- Superpay notifies us of the change in status of each transaction with a separate POST
  request to the /payment-systems/superpay/callback callback
- A 200 response from our side means that the event has been successfully processed. In case of
  a different response status, Superpay will continue to periodically notify about this
  event for N days
- When sending callback requests, Superpay attaches a signature of their contents for
  us to be able to ensure that the request came from them (more details in
  superpay.py)

At the moment, the entry point into the deposit creation scenario is 
`shelter/transactions/services.py::create_deposit`

At the moment, the entry point into the payout creation scenario is 
`shelter/transactions/services.py::create_payout`

## Requirements

- [docker](https://www.docker.io/)
- [docker-compose](https://docs.docker.com/compose/)

## Run tests

`$ make compose-test`
