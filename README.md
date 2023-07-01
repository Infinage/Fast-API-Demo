#### Tech stack

Backend using FAST API (Python)
Frontend using Flutter (Dart)
Database using mongodb

Distribute as a docker containers

#### Notes:

##### Database stuff

config - brand, model, model#, screen size, hdd size, ssd size, Processor Brand, Processor Type, Processor Speed, RAM, Graphics card, OS, Price, warranty, cloned stocks #
stock - serial#, ...config, purchase date, warranty end date, remarks, 
        status { (sold, deleted, new, old (refurbished) ), timestamp },
        current status
sale - serial#, price, sale_date, customer name, mobile, address, remarks
user - username, type, password

_Audit fields_: Created By, Create Date, Updated By, Update Date

##### Modules

0. ~~Add config, clone from existing config, update & delete config~~
1. ~~Add stock: Choose a config, select quantity x. App would create x number of stocks. Each field can be edited manually. Additionally have the option to scan the Serial#~~
2. ~~Sell stock: Choose a serial number, price (add multiple serial# for sale), customer name, customer mobile, address, remarks~~
3. ~~Swap stock: Swap sold stock with unsold stock. Update remarks~~
4. ~~Modify stock: Edit stock details, only admin has this functionality~~
5. ~~Delete stock: Admin only functionality~~
6. ~~View stock details: Dashboard, filters & Reports~~
7. ~~Create / update other users: Owner, Admin, User~~
8. ~~Change password for self~~

##### TODO: 

9. Security for all the APIs created as appropriate
10. Add appropriate API filters for all the GET methods - asset_config, sale
11. Add the created by, updated by fields

##### User Types

1. Owner: Super Admin, has all the access
2. Admin: Access to all except viewing dashboards & reports. Has access to filters though. Can manage only users of type "user"
2. User: Add stock, Sell stock, swap stock

##### Podman Stuff
Running mongo server with podman for development:

podman run --name impression-solutions -v ./db:/data/db -e MONGO_INITDB_ROOT_USERNAME=mongo -e MONGO_INITDB_ROOT_PASSWORD=secret -d mongo

List all podman instances
podman ps -a

Stop the running process
podman stop <name>

Start the container
podman start <name>

Remove the container
podman rm <name>

##### Useful links

1. Farm Stack Chat App: https://github.com/Vitaee/ChatApp/tree/main