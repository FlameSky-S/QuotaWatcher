# QuotaWatcher

`QuotaWatcher` is developed to meet the needs of a over-quota notifying program that is smarter than `warnquota`. The program keeps track of whether it has notified a user or not, and will not repeatedly send mails when called multiple times. So it is safe to schedule a run of `QuotaWatcher` much more frequently without having to worry about bombing users' inbox with tons of mails.

This project is inspired by [asciiphil/quotanotify](https://github.com/asciiphil/quotanotify). Compared to `quotanotify`, `QuotaWatcher` uses mordern dependencies, but is not designed to suit variant needs. As a result, there are no config files included. Feel free to fork this project and modify it for your own use.

- [Features](#Features)
- [Installation](#Installation)
- [Configuration](#Configuration)
- [Related Materials](#Related-Materials)

## Features & Limitations

The program is used together with `quota`, make sure you have quota setup correctly and the `repquota -a` command is working properly.

The program monitors user quota only, there's no support for group quota. Also, only one mount point in quota is supported. That means to use QuotaWatcher, you can set disk quota on one device only.

The program will send an e-mail(or local mail if no e-mail address is configured for the user) to a user only once for each of the following events:

- User exceeds soft-limit
- User exceeds hard-limit

If the user goes back under quota, the notification flag will be reset. The user will be notified if he/she goes over quota again.

You can run this program once every 5 minutes in crontab to notify users in time.

The program is tested on Ubuntu 20.04 with quota version 4.05(`quota --version`).

## Installation

### 1. Prerequisites

- Install postfix and choose "Local only" during configuration.

```shell
# postfix is used to set up local mail service
$ sudo apt install postfix
```

- Install mailutils

```shell
# mailutils is used to send & read mails in command-line environment
$ sudo apt install mailutils
```

### 2. Copy Files

- Clone this repo

```shell
$ git clone https://github.com/FlameSky-S/QuotaWatcher.git
```

- Put the scripts anywhere you want.

```shell
$ mv QuotaWatcher /path/to/destination
```

### 3. Run

Run `main.py` periodically to update databse and send mails to users. You can use crontab, see [below](#2.-Set-up-cronjobs-using-crontab) for an example.

Run `python database.py` to clear all data in database.

## Configuration

Since this project is initially developed for personal use, it's not equipped with a config file. Thus you have to dive into the code and change the settings manually.

### 1. Configure Sender E-mail Address

You'll need a working E-mail account to be able to sent notifications to users via Internet, either real accounts or virtual ones provided by companies like MailTrap. Note that the password needs to be explicitly coded to enable auto login. (Encryption is another option but since the key needs to be stored locally for auto decryption, I think it's easier to just set strict read permissions for the python file on Linux. Disscussion are very much welcomed.)

The sender's address can be altered inside function `write_email` in `main.py`. There is a 'with' block like this:

```python
with smtplib.SMTP_SSL('example.com', 465) as server:
    server.login('username@example.com','password')
    try:
        server.sendmail('username@example.com', user_addr, msg.as_string())
        return 0
    except smtplib.SMTPException as e:
        print(e)
        return 1
```

Also there's a line above this block assigning 'username@example.com' to `msg['From']`. You should change that, too. Settings for different e-mail service providers may differ, please refer to your provider's manual for more details.

### 2. Configure Receiver E-mail Address

QuotaWatcher reads e-mail address of users from an `alias` file. Just fill the file with user-email pairs following the examples given in the file.

### 3. Customize E-mail Content

The e-mail content is assigned inside `write_email` function in `main.py`. There are two versions of e-mail, one for soft limit and the other for hard limit. Alter the content to your liking.

## Related Materials

### 1. Configure postfix and mailutils to use a different path as mailbox

Some administrators may want to restrict the disk usage of `/` directory. In that case, when a user exceeds hard-limit, local mails could not be dilivered because the user cannot create or write any files. A simple workaround would be to change the default mailbox directory to another path on a mounted disk.

- postfix: Add a line in `/etc/postfix/main.cf`, then restart the service:

```text
mail_spool_directory=/path/to/destination
```

Note: Be sure to create the destination folder manually, and change the group permission of that folder to "rws" using `chmod g+s` command.

- mailutils: Create a new file `/etc/mailutils.conf` with the following content:

```text
mailbox {
    mail-spool /path/to/destination;
}
```

### 2. Set up cronjobs using crontab

Run the following command to modify user crontab file. You can also modify the system-wide crontab file `/etc/crontab`, which has a `user` argument before the `command` argument.

```shell
$ crontab -e    # open user crontab file with default editor
```

Append the following line to the end of the file, the example is for user crontab file:

```text
# run QuotaWatcher once every 5 minutes
*/5 * * * * /bin/bash /usr/local/QuotaWatcher/main.py >> /tmp/quotawathcer 2>&1
```

### 3. Setup quota

Follow this [great tutorial](https://wiki.archlinux.org/title/Disk_quota) on ArchLinux to setup disk quota on linux.

<!-- ### 4. Configure -->
