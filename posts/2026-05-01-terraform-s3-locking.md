---
title: "Terraform native S3 locking: what they don't tell you"
date: 2026-05-01
tags: [terraform, aws, iac]
description: "Dropping DynamoDB for state locking in Terraform 1.10+ sounds simple. Here's what bit me."
---

Terraform 1.10 shipped native S3 locking — no more DynamoDB table alongside your state bucket. On paper it's a simplification. In practice there are a few sharp edges worth knowing before you migrate.

## The old setup

The classic pattern was a S3 bucket for state plus a DynamoDB table for locking. Two resources, two IAM policies, two things to Terraform-bootstrap before you could use Terraform. Circular, but manageable.

## What changed

With 1.10+, S3 itself handles the lock via conditional writes. You set `use_lockfile = true` in your backend config and the DynamoDB table is gone.

```hcl
terraform {
  backend "s3" {
    bucket       = "terraform-state-jellyfish-core"
    key          = "core/terraform.tfstate"
    region       = "eu-west-2"
    use_lockfile = true
  }
}
```

## The gotchas

**Bucket policy is stricter than you expect.** The lock mechanism writes a `.tflock` file alongside your state key. If your bucket policy uses `StringNotEquals` conditions on object keys, it will block lock file writes. You need `StringNotEqualsIfExists` or an explicit allow for `*.tflock` keys.

**Existing state files need a migration plan.** If you have a populated state, don't just flip the flag. The lock file path is derived from the state key — run `terraform init` on a clean workspace first and verify the backend reconfigures without error.

**IAM needs `s3:PutObject` on the lock path.** The lock file is a separate S3 object. If your IAM policy scopes `s3:PutObject` to `${bucket_arn}/env:/*` you'll get silent failures. Scope it to `${bucket_arn}/*` or add an explicit statement for `*.tflock`.

**CloudFormation bootstrap still needs care.** If you're using CloudFormation to create the bucket before Terraform runs (reasonable for the chicken-and-egg problem), make sure `ObjectLockEnabled` is not set to `Enabled` — that's S3 Object Lock, not Terraform locking, and they conflict.

## Is it worth migrating?

For new projects, yes — one less resource, one less IAM document. For existing stacks with DynamoDB already in place, the migration risk probably isn't worth it unless you're doing a broader refactor.

The Terraform import commands for getting an existing bucket under management are less obvious than you'd expect. That's a post for another day.
