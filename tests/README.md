| Brief requirement | Test file |
| --- | --- |
| invalid login | `test_auth.py` |
| invalid payment method | `test_payments.py` |
| purchase of more tickets than are available | `test_booking.py` |
| creation of an invalid or overlapping screening | `test_scheduling.py` |
| rollback after a failed transaction | `test_booking.py` |
| concurrent purchase of the last available seat | `test_concurrency.py` |
| one purchase succeeds | `test_concurrency.py` |
| the second purchase fails | `test_concurrency.py` |
| the final number of sold tickets is 10, never 11 | `test_concurrency.py` |
| no partial purchase is stored for the unsuccessful transaction | `test_concurrency.py` |
| the different ticket-pricing rules | `test_pricing.py` |
| clients with different payment methods | `test_data.py` |
| screenings with different levels of availability | `test_data.py` |
| at least one case suitable for testing the booking transaction and concurrency | `test_data.py` |
