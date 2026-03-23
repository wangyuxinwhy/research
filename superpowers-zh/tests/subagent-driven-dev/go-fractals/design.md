# Go 分形 CLI - 设计文档

## 概述

一个生成 ASCII 艺术分形的命令行工具。支持两种分形类型，输出可配置。

## 用法

```bash
# 谢尔宾斯基三角形
fractals sierpinski --size 32 --depth 5

# 曼德博集合
fractals mandelbrot --width 80 --height 24 --iterations 100

# 自定义字符
fractals sierpinski --size 16 --char '#'

# 帮助
fractals --help
fractals sierpinski --help
```

## 命令

### `sierpinski`

使用递归细分法生成谢尔宾斯基三角形（Sierpinski triangle）。

参数：
- `--size`（默认值：32）- 三角形底边的字符宽度
- `--depth`（默认值：5）- 递归深度
- `--char`（默认值：'*'）- 用于填充点的字符

输出：三角形输出到 stdout，每行一行。

### `mandelbrot`

将曼德博集合（Mandelbrot set）渲染为 ASCII 艺术。将迭代次数映射到字符。

参数：
- `--width`（默认值：80）- 输出宽度（字符数）
- `--height`（默认值：24）- 输出高度（字符数）
- `--iterations`（默认值：100）- 逃逸计算的最大迭代次数
- `--char`（默认值：渐变）- 单个字符，或省略以使用渐变 " .:-=+*#%@"

输出：矩形输出到 stdout。

## 架构

```
cmd/
  fractals/
    main.go           # 入口点，CLI 设置
internal/
  sierpinski/
    sierpinski.go     # 算法
    sierpinski_test.go
  mandelbrot/
    mandelbrot.go     # 算法
    mandelbrot_test.go
  cli/
    root.go           # 根命令，帮助
    sierpinski.go     # Sierpinski 子命令
    mandelbrot.go     # Mandelbrot 子命令
```

## 依赖

- Go 1.21+
- `github.com/spf13/cobra` 用于 CLI

## 验收标准

1. `fractals --help` 显示用法
2. `fractals sierpinski` 输出可识别的三角形
3. `fractals mandelbrot` 输出可识别的曼德博集合
4. `--size`、`--width`、`--height`、`--depth`、`--iterations` 参数正常工作
5. `--char` 可自定义输出字符
6. 无效输入产生清晰的错误消息
7. 所有测试通过
