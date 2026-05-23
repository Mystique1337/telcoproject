import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Navbar from "@/components/Navbar";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const signUp = useAuthStore((s) => s.signUp);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signUp(email, password);
      setDone(true);
    } catch (err: any) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="min-h-screen bg-ink-950">
        <Navbar />
        <div className="flex items-center justify-center py-16 px-4">
          <Card className="w-full max-w-md bg-ink-900 border-ink-700 text-center">
            <CardContent className="pt-8 pb-8 space-y-3">
              <p className="text-2xl">✅</p>
              <p className="font-medium text-ink-50">Check your email</p>
              <p className="text-sm text-ink-400">
                We sent a confirmation link to {email}
              </p>
              <Button
                variant="outline"
                className="border-ink-600 text-ink-200"
                onClick={() => navigate("/login")}
              >
                Back to login
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ink-950">
      <Navbar />
      <div className="flex items-center justify-center py-16 px-4">
        <Card className="w-full max-w-md bg-ink-900 border-ink-700">
          <CardHeader>
            <CardTitle className="text-ink-50">Create account</CardTitle>
            <CardDescription className="text-ink-400">
              Get started with InsideNaija
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="email" className="text-ink-200">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-ink-800 border-ink-700 text-ink-50 placeholder:text-ink-500"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="password" className="text-ink-200">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="bg-ink-800 border-ink-700 text-ink-50 placeholder:text-ink-500"
                />
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Button type="submit" className="w-full bg-naija-600 hover:bg-naija-700 text-white" disabled={loading}>
                {loading ? "Creating account…" : "Create account"}
              </Button>
              <p className="text-sm text-center text-ink-400">
                Have an account?{" "}
                <Link to="/login" className="text-naija-400 hover:underline">
                  Sign in
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
