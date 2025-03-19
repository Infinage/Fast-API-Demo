#### Tech stack

- Backend using FAST API (Python) 
- Frontend using Flutter (Dart) 
- Database using mongodb 
- Distribute as a docker containers 

#### Notes:
##### Database Schema

###### **Config**
| Column             | Data Type  |
|--------------------|-----------|
| brand             | TEXT      |
| model             | TEXT      |
| model#            | TEXT      |
| screen_size       | TEXT      |
| hdd_size          | TEXT      |
| ssd_size          | TEXT      |
| processor_brand   | TEXT      |
| processor_type    | TEXT      |
| processor_speed   | TEXT      |
| ram              | TEXT      |
| graphics_card     | TEXT      |
| os               | TEXT      |
| price            | DECIMAL   |
| warranty         | TEXT      |
| cloned_stocks    | INTEGER   |

###### **Stock**
| Column             | Data Type  |
|--------------------|-----------|
| serial#           | TEXT (Primary Key) |
| ...config         | (References `config`) |
| purchase_date     | DATE      |
| warranty_end_date | DATE      |
| remarks          | TEXT      |
| status           | ENUM ('sold', 'deleted', 'new', 'old (refurbished)') |
| timestamp        | TIMESTAMP |
| current_status   | TEXT      |

###### **Sale**
| Column       | Data Type  |
|-------------|-----------|
| serial#     | TEXT (Foreign Key -> Stock) |
| price       | DECIMAL   |
| sale_date   | DATE      |
| customer_name | TEXT    |
| mobile      | TEXT      |
| address     | TEXT      |
| remarks     | TEXT      |

###### **User**
| Column   | Data Type  |
|----------|-----------|
| username | TEXT (Primary Key) |
| type     | TEXT (e.g., 'admin', 'sales') |
| password | TEXT      |

###### **Audit Fields (Common for All Tables)**
| Column       | Data Type  |
|-------------|-----------|
| created_by  | TEXT (Foreign Key -> User) |
| create_date | TIMESTAMP |
| updated_by  | TEXT (Foreign Key -> User) |
| update_date | TIMESTAMP |

##### TODO

0. ~~Add config, clone from existing config, update & delete config~~
1. ~~Add stock: Choose a config, select quantity x. App would create x number of stocks. Each field can be edited manually. Additionally have the option to scan the Serial#~~
2. ~~Sell stock: Choose a serial number, price (add multiple serial# for sale), customer name, customer mobile, address, remarks~~
3. ~~Swap stock: Swap sold stock with unsold stock. Update remarks~~
4. ~~Modify stock: Edit stock details, only admin has this functionality~~
5. ~~Delete stock: Admin only functionality~~
6. ~~View stock details: Dashboard, filters & Reports~~
7. ~~Create / update other users: Owner, Admin, User~~
8. ~~Change password for self~~
9. ~~Security for all the APIs created as appropriate~~
10. ~~Add appropriate API filters for all the GET methods~~
11. ~~Add the created by, updated by fields~~

##### User Types

1. Owner: Super Admin, has all the access
2. Admin: Access to all except viewing dashboards & reports. Has access to filters though. Can manage only users of type "user"
2. User: Add stock, Sell stock, swap stock

##### Getting started:

docker-compose --env-file ./backend/.env
