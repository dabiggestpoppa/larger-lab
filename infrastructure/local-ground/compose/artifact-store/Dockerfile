# syntax=docker/dockerfile:1.7
FROM docker.io/library/golang:1.22.2-alpine3.19@sha256:d95b4ffda07936e6f302209a7a7912855b8659d2439af3e48939fc7f5c330716 AS build

ARG RELEASE_TAG=RELEASE.2024-05-28T17-19-04Z
ARG SOURCE_COMMIT=f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531
ARG SOURCE_SHA256=558275de8aaf5fa04cca55cfd712ea76886e34b47458a591e2754b3caeaab2c3
ARG SHORT_COMMIT=f79a4ef4d0dc

ADD --checksum=sha256:${SOURCE_SHA256} \
    https://codeload.github.com/minio/minio/tar.gz/${SOURCE_COMMIT} \
    /tmp/minio-source.tar.gz
RUN mkdir -p /src && tar -xzf /tmp/minio-source.tar.gz -C /src \
    && mv "/src/minio-${SOURCE_COMMIT}" /src/minio \
    && test "$(sha256sum /tmp/minio-source.tar.gz | awk '{print $1}')" = "${SOURCE_SHA256}" \
    && test -s /src/minio/go.sum
WORKDIR /src/minio
RUN CGO_ENABLED=0 GOPROXY=https://proxy.golang.org,direct GOSUMDB=sum.golang.org \
    go build -mod=readonly -tags kqueue -trimpath \
    -ldflags="-s -w \
      -X github.com/minio/minio/cmd.Version=${RELEASE_TAG} \
      -X github.com/minio/minio/cmd.CopyrightYear=2024 \
      -X github.com/minio/minio/cmd.ReleaseTag=${RELEASE_TAG} \
      -X github.com/minio/minio/cmd.CommitID=${SOURCE_COMMIT} \
      -X github.com/minio/minio/cmd.ShortCommitID=${SHORT_COMMIT}" \
    -o /out/minio . \
    && /out/minio --version | grep -F "${RELEASE_TAG}"

FROM docker.io/library/alpine:3.20.1@sha256:ac77ebc035f69184acb2660028580c9053f6d0f892de7933e1456d8b5e0ac085

ARG RELEASE_TAG=RELEASE.2024-05-28T17-19-04Z
ARG SOURCE_COMMIT=f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531
RUN apk add --no-cache ca-certificates=20241121-r1 curl=8.12.1-r0
COPY --from=build /out/minio /usr/bin/minio
COPY --from=build /src/minio/dockerscripts/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
COPY --from=build /src/minio/LICENSE /licenses/LICENSE
COPY --from=build /src/minio/CREDITS /licenses/CREDITS
RUN chmod 0755 /usr/bin/docker-entrypoint.sh \
    && /usr/bin/minio --version | grep -F "${RELEASE_TAG}"
LABEL org.opencontainers.image.source="https://github.com/minio/minio" \
      org.opencontainers.image.version="${RELEASE_TAG}" \
      org.opencontainers.image.revision="${SOURCE_COMMIT}" \
      org.opencontainers.image.licenses="AGPL-3.0-only"
EXPOSE 9000 9001
VOLUME ["/data"]
ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
CMD ["minio"]
