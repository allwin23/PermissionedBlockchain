FROM golang:1.22 AS builder

ARG CC_SERVER_PORT=9999
WORKDIR /opt/chaincode

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /chaincode .

FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /chaincode /chaincode

EXPOSE 9999
ENTRYPOINT ["/chaincode"]