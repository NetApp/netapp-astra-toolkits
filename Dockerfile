FROM ubuntu:jammy

ARG HELM_VERSION=3.11.1
ARG KUBECTL_VERSION=1.24.10
ARG KUSTOMIZE_VERSION=v5.0.0
ARG KUBESEAL_VERSION=v0.18.4
ARG EKSCTL_VERSION=v0.129.0
ARG AWS_IAM_AUTH_VERSION=0.5.9

RUN apt-get update && \
    apt-get -y --no-install-recommends install ca-certificates curl apt-transport-https lsb-release gnupg jq git python3-pip zip unzip && \
    apt-get autoremove -y && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Install helm, helm-diff, and helm-unittest
ENV BASE_URL="https://get.helm.sh"
ENV TAR_FILE="helm-v${HELM_VERSION}-linux-amd64.tar.gz"
RUN curl -sL ${BASE_URL}/${TAR_FILE} | tar -xvz && \
    mv linux-amd64/helm /usr/bin/helm && \
    chmod +x /usr/bin/helm && \
    rm -rf linux-amd64 && \
    helm plugin install https://github.com/databus23/helm-diff && rm -rf /tmp/helm-* && \
    helm plugin install https://github.com/quintush/helm-unittest && rm -rf /tmp/helm-*

# Install kubectl, kustomize, and kubeseal
RUN curl -sLO https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
    mv kubectl /usr/bin/kubectl && \
    chmod +x /usr/bin/kubectl && \
    curl -sLO https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz && \
    tar xvzf kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz && \
    mv kustomize /usr/bin/kustomize && \
    chmod +x /usr/bin/kustomize && \
    curl -sL https://github.com/bitnami-labs/sealed-secrets/releases/download/${KUBESEAL_VERSION}/kubeseal-linux-amd64 -o kubeseal && \
    mv kubeseal /usr/bin/kubeseal && \
    chmod +x /usr/bin/kubeseal

# Install aws-iam-authenticator, eksctl, and awscli
RUN curl -Lo aws-iam-authenticator https://github.com/kubernetes-sigs/aws-iam-authenticator/releases/download/v${AWS_IAM_AUTH_VERSION}/aws-iam-authenticator_${AWS_IAM_AUTH_VERSION}_linux_amd64 && \
    mv aws-iam-authenticator /usr/bin/aws-iam-authenticator && \
    chmod +x /usr/bin/aws-iam-authenticator && \
    curl -sL "https://github.com/weaveworks/eksctl/releases/download/${EKSCTL_VERSION}/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp && \
    mv /tmp/eksctl /usr/bin && \
    chmod +x /usr/bin/eksctl && \
    curl -Lo awscliv2.zip https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip && \
    unzip awscliv2.zip -d /tmp && \
    /tmp/aws/install -i /usr/local/aws-cli -b /usr/local/bin

# Install gcloud
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get -y --no-install-recommends install google-cloud-cli && \
    apt-get autoremove -y && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Install az
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sed "s/apt-get install -y/apt-get install -y --no-install-recommends/g" | bash && \
    apt-get autoremove -y && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Install actoolkit
RUN pip3 install --upgrade pip && \
    pip3 install virtualenv && \
    pip3 install actoolkit && \
    pip3 cache purge && \
    ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /apps
