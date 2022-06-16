BASE_VERSION := $(shell cat 'version.txt')
BUILD_DATE := $(shell date '+%Y%m%d%H%M')

BUILD_VERSION := ${BASE_VERSION}.${BUILD_DATE}
ifndef IMAGE_TAG
	IMAGE_TAG := ${BUILD_VERSION}
endif

all: build push

build:
	docker build -f Dockerfile . --tag netapp/astra-toolkit:${IMAGE_TAG}
	docker tag netapp/astra-toolkit:${IMAGE_TAG} netapp/astra-toolkit:${BASE_VERSION}
	docker tag netapp/astra-toolkit:${IMAGE_TAG} netapp/astra-toolkit:latest
push:
	docker push netapp/astra-toolkit:${IMAGE_TAG}
	docker push netapp/astra-toolkit:${BASE_VERSION}
	docker push netapp/astra-toolkit:latest
