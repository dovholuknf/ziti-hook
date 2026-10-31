FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod go.sum main.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o /ziti-hook .

FROM scratch
COPY --from=build /ziti-hook /ziti-hook
ENTRYPOINT ["/ziti-hook"]
