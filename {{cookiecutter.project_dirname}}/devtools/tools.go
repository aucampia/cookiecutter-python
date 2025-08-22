//go:build tools
// +build tools

package root

//nolint:golint
import (
	_ "github.com/go-task/task/v3/cmd/task"   // toolchain
	_ "github.com/google/yamlfmt/cmd/yamlfmt" // toolchain
	_ "mvdan.cc/sh/v3/cmd/shfmt"              // toolchain
)
