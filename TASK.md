Task - integrate with the SuperPay payment system.

They currently provide the following API.

Deposit:
```
POST http://superpay.com/api/deposit
{
            'description’: ’some transaction description',

            'amount': 12.33,

            'currency': ‘RUB’,

            'redirect_success_url': ‘https://example.com/superpay?result=success',

            'redirect_failure_url': ‘https://example.com/superpay?result=failure',

            'locale': 'en',

            ‘merchant_id': 1234567,
        }
```
merchant_id is the transaction ID on our side (on the example.com website)

Withdrawal:
```
POST http://superpay.com/api/payout

{

            'description’: ’some transaction description',

            'amount': 22.34,

            'currency': ‘USD’,

            ‘wallet_id’: <superpay wallet id>,

            ‘merchant_id': 1234568,

        }
```

When a user withdraws funds, he specifies the amount and the wallet associated
with wallet_id at SuperPay. Superpay does not have documentation for API
responses and callback formats. They claim that they will implement any forms of
responses and callbacks that will be convenient for our (example.com)
integration . It can be assumed that they have the necessary transaction data
(time of transaction, success/failure, etc.). Wallets within SuperPay are
considered multi-currency.

1. Prepare a technical specification for the SuperPay team to modify/improve the API for our product, example.com. Clarify any ambiguities in their API (clarification involves compiling a list of questions, as SuperPay is a fictional system).
2. Develop the relational database structure to store all necessary data within the SuperPay integration. Assume that the User model already exists. Assume everything is in place for tracking fund movements within user wallets (i.e., user has Wallet, and we don't delve into wallet.deposit_amount, wallet.hold_amount, wallet.withdraw_amount calls, but a description of the Wallet model is required). Assume Django ORM is available.
3. Assume the necessary infrastructure is available (describe what is needed). For example, a cron job in the system is ready to execute the required logic on schedule. Or assume there is a queue/worker, and a task can be set in the worker using the set_task command, and the task can be obtained and executed in the worker using the get_task command (task - Python function).
4. Write code for fund withdrawal (HTTP API handler code, processing withdrawal requests and callbacks from SuperPay) + additional code if something needs to be executed besides our HTTP API code. When implementing, we don't delve into secondary matters - if there is a desire to show that some auxiliary logic needs to be called in some place, it's sufficient to simply write do_something_cool_here(a=1, b=2) without implementing the logic itself.
5. Write tests (pytest) for some important part of the written code. We don't need all tests (it takes significant time), but we need to cover something important so that we can see the implementation of tests.
6. As a result of completing the task, there will be no actual executable code, just a set of files/modules containing various parts of code (HTTP API, internal wallet logic, logic of some workers). However, the written code should provide an understanding of the correctness of the approach, cleanliness, and quality of the tests.
7. Describe the flow, architecture simply in text. No need to spend time on graphics.

If a detail is not described in the task above - you can choose a more
correct/convenient option.
