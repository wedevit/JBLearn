# CodeSandbox supports debian & ubuntu based images
FROM ubuntu
 
# Example; install htop by default
RUN apt update -y && apt install -y htop

# The project will be mounted in /workspace by default

# Every new shell will open inside the built container

# On top of this build, we install `zsh`, `git` and `docker` as additional
# Docker layers.


# Install PHP & Composer
RUN apt update -y && DEBIAN_FRONTEND=noninteractive apt install -y curl php-cli php-mbstring git unzip && \
  cd ~ && \
  curl -sS https://getcomposer.org/installer -o composer-setup.php && \
  php composer-setup.php --install-dir=/usr/local/bin --filename=composer && \
  composer --version


# Install Node v16 and NPM
RUN apt update -y && apt install -y curl && \
  curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
  apt update -y && apt install -y nodejs


RUN apt update && apt install -y python3 python3-pip
